import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { WebsocketService } from '../../../services/websocket.service';

interface LogLine {
  level: string;
  message: string;
  timestamp: string;
}

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss'
})
export class LogsComponent implements OnInit, OnDestroy {
  logs: LogLine[] = [];
  level = '';
  connected = false;
  readonly levels = ['info', 'warning', 'error'];
  private subscription?: Subscription;

  constructor(private websocketService: WebsocketService) {}

  ngOnInit(): void {
    // Le serveur renvoie les 10 derniers logs Redis chaque seconde.
    this.subscription = this.websocketService.getLogs().subscribe({
      next: (data) => {
        this.connected = true;
        if (data?.logs) this.logs = data.logs;
      },
      error: () => (this.connected = false),
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  get visible(): LogLine[] {
    return this.level ? this.logs.filter((log) => this.normalize(log.level) === this.level) : this.logs;
  }

  normalize(level: string): string {
    const value = String(level || '').toLowerCase();
    return value === 'critical' ? 'error' : value;
  }

  tone(level: string): string {
    return { info: 'info', warning: 'warning', error: 'danger' }[this.normalize(level)] ?? 'secondary';
  }
}
