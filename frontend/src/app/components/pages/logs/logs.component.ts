import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, Subscription, debounceTime } from 'rxjs';
import { WebsocketService } from '../../../services/websocket.service';
import { LogLine, LogsService } from '../../../services/logs.service';

type Tab = 'live' | 'history';

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss'
})
export class LogsComponent implements OnInit, OnDestroy {
  tab: Tab = 'live';
  level = '';
  readonly levels = ['info', 'warning', 'error'];

  // En direct : logs encore dans Redis (5 dernières minutes environ).
  liveLogs: LogLine[] = [];
  connected = false;

  // Historique : logs archivés dans MongoDB.
  history: LogLine[] = [];
  historyTotal = 0;
  historyQuery = '';
  historyLoading = false;
  historyError = false;
  private readonly pageSize = 50;
  private readonly search$ = new Subject<void>();
  private subscriptions = new Subscription();

  constructor(private websocketService: WebsocketService, private logsService: LogsService) {}

  ngOnInit(): void {
    // Le serveur renvoie les 50 logs les plus récents de Redis chaque seconde.
    this.subscriptions.add(this.websocketService.getLogs().subscribe({
      next: (data) => {
        this.connected = true;
        if (data?.logs) this.liveLogs = data.logs;
      },
      error: () => (this.connected = false),
    }));
    this.subscriptions.add(this.search$.pipe(debounceTime(300)).subscribe(() => this.loadHistory()));
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  selectTab(tab: Tab): void {
    this.tab = tab;
    if (tab === 'history' && !this.history.length) this.loadHistory();
  }

  selectLevel(level: string): void {
    this.level = level;
    if (this.tab === 'history') this.loadHistory();
  }

  onSearch(): void {
    this.search$.next();
  }

  loadHistory(append = false): void {
    this.historyLoading = true;
    this.historyError = false;
    this.logsService.getHistory({
      level: this.level || undefined,
      q: this.historyQuery.trim() || undefined,
      skip: append ? this.history.length : 0,
      limit: this.pageSize,
    }).subscribe({
      next: (page) => {
        this.history = append ? [...this.history, ...page.logs] : page.logs;
        this.historyTotal = page.total;
        this.historyLoading = false;
      },
      error: () => {
        this.historyLoading = false;
        this.historyError = true;
      },
    });
  }

  get visibleLive(): LogLine[] {
    return this.level ? this.liveLogs.filter((log) => this.normalize(log.level) === this.level) : this.liveLogs;
  }

  get canLoadMore(): boolean {
    return this.history.length < this.historyTotal;
  }

  normalize(level: string): string {
    const value = String(level || '').toLowerCase();
    return value === 'critical' ? 'error' : value;
  }

  tone(level: string): string {
    return ({ info: 'info', warning: 'warning', error: 'danger' } as Record<string, string>)[this.normalize(level)] ?? 'secondary';
  }
}
