import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import {
  Payment,
  PaymentsStore,
  customerName,
  formatAmount,
  isAnomaly,
  providerLabel,
  sourceOf,
  statusOf,
} from '../../../services/payments-store.service';

type Period = 'all' | 'today' | '7d' | '30d';

@Component({
  selector: 'app-transactions',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './transactions.component.html',
  styleUrl: './transactions.component.scss'
})
export class TransactionsComponent implements OnInit, OnDestroy {
  all: Payment[] = [];
  rows: Payment[] = [];
  page = 1;
  readonly pageSize = 15;

  query = '';
  status = '';
  source = '';
  provider = '';
  period: Period = 'all';
  anomaliesOnly = false;

  readonly formatAmount = formatAmount;
  readonly statusOf = statusOf;
  readonly customerName = customerName;
  readonly providerLabel = providerLabel;
  readonly sourceOf = sourceOf;
  readonly isAnomaly = isAnomaly;

  private subscriptions = new Subscription();

  constructor(private store: PaymentsStore, private route: ActivatedRoute) {}

  ngOnInit(): void {
    this.store.load();
    // ?q=… : recherche lancée depuis la barre du haut.
    this.subscriptions.add(this.route.queryParamMap.subscribe((params) => {
      this.query = params.get('q') ?? this.query;
      this.applyFilters();
    }));
    this.subscriptions.add(this.store.payments.subscribe((payments) => {
      this.all = payments;
      this.applyFilters(false);
    }));
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  applyFilters(resetPage = true): void {
    const needle = this.query.trim().toLowerCase();
    const since = this.periodStart();
    this.rows = this.all.filter((p) => {
      if (this.status && p.status !== this.status) return false;
      if (this.source && sourceOf(p) !== this.source) return false;
      if (this.provider && providerLabel(p) !== this.provider) return false;
      if (this.anomaliesOnly && !isAnomaly(p)) return false;
      if (since && (!p.created_at || new Date(p.created_at) < since)) return false;
      if (!needle) return true;
      return [p.id, p.order_reference, customerName(p), p.customer_email, p.user_id]
        .some((value) => String(value ?? '').toLowerCase().includes(needle));
    });
    if (resetPage) this.page = 1;
    this.page = Math.min(this.page, this.pageCount);
  }

  reset(): void {
    this.query = '';
    this.status = '';
    this.source = '';
    this.provider = '';
    this.period = 'all';
    this.anomaliesOnly = false;
    this.applyFilters();
  }

  get hasFilters(): boolean {
    return !!(this.query || this.status || this.source || this.provider || this.anomaliesOnly || this.period !== 'all');
  }

  get pageCount(): number {
    return Math.max(1, Math.ceil(this.rows.length / this.pageSize));
  }

  get visible(): Payment[] {
    return this.rows.slice((this.page - 1) * this.pageSize, this.page * this.pageSize);
  }

  get providers(): string[] {
    return [...new Set(this.all.map(providerLabel))].sort();
  }

  /** Totaux du filtre courant, par devise (MGA et USD ne s'additionnent pas). */
  get totals(): { currency: string; paid: number; count: number }[] {
    const byCurrency = new Map<string, { currency: string; paid: number; count: number }>();
    for (const p of this.rows) {
      const entry = byCurrency.get(p.currency) ?? { currency: p.currency, paid: 0, count: 0 };
      entry.count++;
      if (p.status === 'success') entry.paid += Number(p.amount || 0);
      byCurrency.set(p.currency, entry);
    }
    return [...byCurrency.values()].sort((a, b) => Number(b.currency === 'MGA') - Number(a.currency === 'MGA'));
  }

  exportCsv(): void {
    const header = ['Date', 'Origine', 'Référence', 'Client', 'Montant', 'Devise', 'Moyen', 'Statut', 'Prédiction', 'ID'];
    const lines = this.rows.map((p) => [
      p.created_at ?? '',
      sourceOf(p),
      p.order_reference ?? '',
      customerName(p),
      p.amount,
      p.currency,
      providerLabel(p),
      statusOf(p).label,
      isAnomaly(p) ? 'Anomalie' : p.prediction ? 'Normal' : '',
      p.id,
    ]);
    const escape = (value: unknown) => `"${String(value).replace(/"/g, '""')}"`;
    const csv = [header, ...lines].map((line) => line.map(escape).join(';')).join('\r\n');
    // BOM : accents corrects à l'ouverture dans Excel.
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `transactions-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  trackById(_: number, payment: Payment): string {
    return payment.id;
  }

  private periodStart(): Date | null {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    switch (this.period) {
      case 'today': return startOfToday;
      case '7d': return new Date(startOfToday.getTime() - 6 * 86_400_000);
      case '30d': return new Date(startOfToday.getTime() - 29 * 86_400_000);
      default: return null;
    }
  }
}
