import { Component, OnInit } from '@angular/core';
import { AsyncPipe, CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { map } from 'rxjs';
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

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, AsyncPipe, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  readonly stats$ = this.store.stats;
  readonly loading$ = this.store.loading;
  readonly latest$ = this.store.payments.pipe(map((rows) => rows.slice(0, 6)));

  readonly formatAmount = formatAmount;
  readonly statusOf = statusOf;
  readonly customerName = customerName;
  readonly providerLabel = providerLabel;
  readonly sourceOf = sourceOf;
  readonly isAnomaly = isAnomaly;

  constructor(private store: PaymentsStore) {}

  ngOnInit(): void {
    this.store.load();
  }

  refresh(): void {
    this.store.load(true);
  }

  /** Hauteur d'une barre en % de la journée la plus chargée. */
  barHeight(value: number, values: { count: number }[]): number {
    const max = Math.max(1, ...values.map((v) => v.count));
    return Math.round((value / max) * 100);
  }

  share(part: number, total: number): number {
    return total ? Math.round((part / total) * 100) : 0;
  }

  trackByLabel(_: number, row: { label: string }): string {
    return row.label;
  }

  trackById(_: number, payment: Payment): string {
    return payment.id;
  }
}
