import * as vscode from 'vscode';

const DAEMON_BASE_URL = 'http://127.0.0.1:8765';

type TelemetryEventType = 'cursor' | 'text_change' | 'document_open' | 'document_save' | 'heartbeat';

type TextChangeDelta = {
  range_start_line: number;
  range_start_character: number;
  range_end_line: number;
  range_end_character: number;
  text: string;
};

type TelemetryStreamEvent = {
  session_id: string;
  event_type: TelemetryEventType;
  file_path: string;
  language_id: string;
  sequence_id: number;
  document_version?: number;
  cursor_line?: number;
  cursor_column?: number;
  full_text?: string;
  symbol_path: string[];
  deltas: TextChangeDelta[];
  metadata: Record<string, unknown>;
};

const sessionId = `vscode-${Date.now()}`;
let telemetryBuffer: TelemetryStreamEvent[] = [];
let flushTimer: NodeJS.Timeout | undefined;
const fileSequence = new Map<string, number>();
const fileChangeCounter = new Map<string, number>();
const pendingResyncFiles = new Set<string>();

function nextSequence(filePath: string): number {
  const value = (fileSequence.get(filePath) ?? 0) + 1;
  fileSequence.set(filePath, value);
  return value;
}

function warn(message: string): void {
  void vscode.window.showWarningMessage(message);
}

function getTelemetryConfig(): {
  tickMs: number;
  maxBatchSize: number;
  enabled: boolean;
  hardBufferLimit: number;
  heartbeatEveryNChanges: number;
} {
  const cfg = vscode.workspace.getConfiguration('loraJit.telemetry');
  return {
    tickMs: cfg.get<number>('tickMs', 75),
    maxBatchSize: cfg.get<number>('maxBatchSize', 200),
    enabled: cfg.get<boolean>('enabled', true),
    hardBufferLimit: cfg.get<number>('hardBufferLimit', 1000),
    heartbeatEveryNChanges: cfg.get<number>('heartbeatEveryNChanges', 40)
  };
}

async function resolveActiveSymbolPath(
  document: vscode.TextDocument,
  position: vscode.Position | undefined
): Promise<string[]> {
  if (!position) {
    return [];
  }

  try {
    const symbols = await vscode.commands.executeCommand<vscode.DocumentSymbol[]>(
      'vscode.executeDocumentSymbolProvider',
      document.uri
    );
    if (!symbols || symbols.length === 0) {
      return [];
    }

    const path: string[] = [];
    const walk = (nodes: vscode.DocumentSymbol[], stack: string[]): boolean => {
      for (const node of nodes) {
        if (!node.range.contains(position)) {
          continue;
        }

        const nextStack = [...stack, node.name];
        if (walk(node.children, nextStack)) {
          return true;
        }

        path.splice(0, path.length, ...nextStack);
        return true;
      }

      return false;
    };

    walk(symbols, []);
    return path;
  } catch {
    return [];
  }
}

function buildHeartbeatEvent(document: vscode.TextDocument): TelemetryStreamEvent {
  return {
    ...buildBaseEvent('heartbeat', document),
    sequence_id: nextSequence(document.fileName),
    deltas: [],
    symbol_path: [],
    full_text: document.getText(),
    metadata: { source: 'vscode-extension', heartbeat: true }
  };
}

function flushTelemetryNow(): void {
  const { enabled } = getTelemetryConfig();
  if (!enabled || telemetryBuffer.length === 0) {
    return;
  }

  const payload = { events: telemetryBuffer };
  telemetryBuffer = [];

  void fetch(`${DAEMON_BASE_URL}/telemetry/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(async (response) => {
      if (!response.ok) {
        return;
      }

      const body = (await response.json()) as { resync_files?: string[] };
      const resyncFiles = body.resync_files ?? [];
      if (resyncFiles.length === 0) {
        return;
      }

      resyncFiles.forEach((filePath) => pendingResyncFiles.add(filePath));
      for (const editor of vscode.window.visibleTextEditors) {
        if (!pendingResyncFiles.has(editor.document.fileName)) {
          continue;
        }
        enqueueTelemetry(buildHeartbeatEvent(editor.document));
        pendingResyncFiles.delete(editor.document.fileName);
      }
    })
    .catch(() => {
      // Fire-and-forget by design: do not block editor thread.
    });
}

function scheduleTelemetryFlush(): void {
  if (flushTimer) {
    return;
  }

  const { tickMs } = getTelemetryConfig();
  flushTimer = setTimeout(() => {
    flushTimer = undefined;
    flushTelemetryNow();
  }, Math.max(25, tickMs));
}

function enqueueTelemetry(event: TelemetryStreamEvent): void {
  const { enabled, maxBatchSize, hardBufferLimit } = getTelemetryConfig();
  if (!enabled) {
    return;
  }

  if (telemetryBuffer.length >= Math.max(100, hardBufferLimit)) {
    telemetryBuffer = [];
    warn('LoRA-JIT telemetry buffer limit reached. Dropping queued events to protect editor memory.');
  }

  telemetryBuffer.push(event);
  if (telemetryBuffer.length >= Math.max(10, maxBatchSize)) {
    flushTelemetryNow();
    return;
  }

  scheduleTelemetryFlush();
}

function buildBaseEvent(
  eventType: TelemetryEventType,
  document: vscode.TextDocument
): Omit<TelemetryStreamEvent, 'deltas' | 'sequence_id' | 'full_text'> {
  return {
    session_id: sessionId,
    event_type: eventType,
    file_path: document.fileName,
    language_id: document.languageId,
    document_version: document.version,
    symbol_path: [],
    metadata: { source: 'vscode-extension' }
  };
}

async function pingDaemon(): Promise<void> {
  try {
    const response = await fetch(`${DAEMON_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Daemon returned ${response.status}`);
    }

    const body = (await response.json()) as { status?: string };
    vscode.window.showInformationMessage(`LoRA-JIT daemon status: ${body.status ?? 'unknown'}`);
  } catch (error) {
    vscode.window.showErrorMessage(`LoRA-JIT daemon unreachable: ${String(error)}`);
  }
}

async function sendSampleTelemetry(): Promise<void> {
  const payload = {
    session_id: 'vscode-session',
    file_path: vscode.window.activeTextEditor?.document.fileName ?? 'unknown',
    language_id: vscode.window.activeTextEditor?.document.languageId ?? 'unknown',
    cursor_line: vscode.window.activeTextEditor?.selection.active.line ?? 0,
    cursor_column: vscode.window.activeTextEditor?.selection.active.character ?? 0,
    symbols_in_scope: [],
    metadata: { source: 'vscode-extension' }
  };

  try {
    const response = await fetch(`${DAEMON_BASE_URL}/telemetry/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Route call failed: ${response.status}`);
    }

    const body = (await response.json()) as { adapter_id?: string; confidence?: number };
    vscode.window.showInformationMessage(
      `LoRA-JIT route: ${body.adapter_id ?? 'n/a'} (${body.confidence ?? 0})`
    );
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to send LoRA-JIT telemetry: ${String(error)}`);
  }
}

function wireLiveTelemetry(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      enqueueTelemetry({
        ...buildBaseEvent('document_open', document),
        sequence_id: nextSequence(document.fileName),
        full_text: document.getText(),
        deltas: []
      });
    }),
    vscode.workspace.onDidSaveTextDocument((document) => {
      enqueueTelemetry({
        ...buildBaseEvent('document_save', document),
        sequence_id: nextSequence(document.fileName),
        full_text: document.getText(),
        deltas: []
      });
    }),
    vscode.workspace.onDidChangeTextDocument((event) => {
      const deltas: TextChangeDelta[] = event.contentChanges.map((change) => ({
        range_start_line: change.range.start.line,
        range_start_character: change.range.start.character,
        range_end_line: change.range.end.line,
        range_end_character: change.range.end.character,
        text: change.text
      }));

      const filePath = event.document.fileName;
      const count = (fileChangeCounter.get(filePath) ?? 0) + 1;
      fileChangeCounter.set(filePath, count);

      enqueueTelemetry({
        ...buildBaseEvent('text_change', event.document),
        sequence_id: nextSequence(filePath),
        deltas,
        metadata: {
          source: 'vscode-extension',
          reason: event.reason
        }
      });

      const { heartbeatEveryNChanges } = getTelemetryConfig();
      if (count % Math.max(5, heartbeatEveryNChanges) === 0) {
        enqueueTelemetry(buildHeartbeatEvent(event.document));
      }
    }),
    vscode.window.onDidChangeTextEditorSelection((event) => {
      const active = event.selections[0]?.active;
      if (!active) {
        return;
      }

      void resolveActiveSymbolPath(event.textEditor.document, active).then((symbolPath) => {
        enqueueTelemetry({
          ...buildBaseEvent('cursor', event.textEditor.document),
          sequence_id: nextSequence(event.textEditor.document.fileName),
          cursor_line: active.line,
          cursor_column: active.character,
          symbol_path: symbolPath,
          deltas: [],
          metadata: {
            source: 'vscode-extension',
            semantic_context: symbolPath.join('::')
          }
        });
      });
    })
  );
}

export function activate(context: vscode.ExtensionContext): void {
  wireLiveTelemetry(context);

  context.subscriptions.push(
    vscode.commands.registerCommand('lora-jit.pingDaemon', pingDaemon),
    vscode.commands.registerCommand('lora-jit.sendSampleTelemetry', sendSampleTelemetry)
  );
}

export function deactivate(): void {
  if (flushTimer) {
    clearTimeout(flushTimer);
    flushTimer = undefined;
  }
  flushTelemetryNow();
}
