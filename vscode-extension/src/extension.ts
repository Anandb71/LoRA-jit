import * as vscode from 'vscode';

const DAEMON_BASE_URL = 'http://127.0.0.1:8765';

type TelemetryEventType = 'cursor' | 'text_change' | 'document_open' | 'document_save';

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
  document_version?: number;
  cursor_line?: number;
  cursor_column?: number;
  deltas: TextChangeDelta[];
  metadata: Record<string, unknown>;
};

const sessionId = `vscode-${Date.now()}`;
let telemetryBuffer: TelemetryStreamEvent[] = [];
let flushTimer: NodeJS.Timeout | undefined;

function getTelemetryConfig(): { tickMs: number; maxBatchSize: number; enabled: boolean } {
  const cfg = vscode.workspace.getConfiguration('loraJit.telemetry');
  return {
    tickMs: cfg.get<number>('tickMs', 75),
    maxBatchSize: cfg.get<number>('maxBatchSize', 200),
    enabled: cfg.get<boolean>('enabled', true)
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
  }).catch(() => {
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
  const { enabled, maxBatchSize } = getTelemetryConfig();
  if (!enabled) {
    return;
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
): Omit<TelemetryStreamEvent, 'deltas'> {
  return {
    session_id: sessionId,
    event_type: eventType,
    file_path: document.fileName,
    language_id: document.languageId,
    document_version: document.version,
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
      enqueueTelemetry({ ...buildBaseEvent('document_open', document), deltas: [] });
    }),
    vscode.workspace.onDidSaveTextDocument((document) => {
      enqueueTelemetry({ ...buildBaseEvent('document_save', document), deltas: [] });
    }),
    vscode.workspace.onDidChangeTextDocument((event) => {
      const deltas: TextChangeDelta[] = event.contentChanges.map((change) => ({
        range_start_line: change.range.start.line,
        range_start_character: change.range.start.character,
        range_end_line: change.range.end.line,
        range_end_character: change.range.end.character,
        text: change.text
      }));

      enqueueTelemetry({
        ...buildBaseEvent('text_change', event.document),
        deltas,
        metadata: {
          source: 'vscode-extension',
          reason: event.reason
        }
      });
    }),
    vscode.window.onDidChangeTextEditorSelection((event) => {
      const active = event.selections[0]?.active;
      if (!active) {
        return;
      }

      enqueueTelemetry({
        ...buildBaseEvent('cursor', event.textEditor.document),
        cursor_line: active.line,
        cursor_column: active.character,
        deltas: []
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
