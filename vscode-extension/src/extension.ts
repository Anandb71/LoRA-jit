import * as vscode from 'vscode';

const DAEMON_BASE_URL = 'http://127.0.0.1:8765';

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

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand('lora-jit.pingDaemon', pingDaemon),
    vscode.commands.registerCommand('lora-jit.sendSampleTelemetry', sendSampleTelemetry)
  );
}

export function deactivate(): void {
  // no-op for MVP
}
