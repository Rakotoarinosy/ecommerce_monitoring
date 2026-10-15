import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable, map } from 'rxjs';
import { PaymentService } from './payement.service';
import { WebsocketService } from './websocket.service';

export interface Payment {
  id: string;
  user_id?: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string | null;
  source?: string;
  provider?: string | null;
  order_reference?: string | null;
  customer_name?: string | null;
  customer_email?: string | null;
  prediction?: string;
}

export interface DayBucket {
  label: string;
  count: number;
  paidMga: number;
}

export interface PaymentStats {
  total: number;
  paid: number;
  pending: number;
  failed: number;
  cancelled: number;
  successRate: number;
  anomalies: number;
  paidMga: number;
  paidUsd: number;
  averageMga: number;
  bySource: { label: string; count: number }[];
  last14Days: DayBucket[];
}

/** Liste des paiements partagée par les pages (chargée une fois, tenue à jour par WebSocket). */
@Injectable({ providedIn: 'root' })
export class PaymentsStore {
  private readonly payments$ = new BehaviorSubject<Payment[]>([]);
  private readonly loading$ = new BehaviorSubject<boolean>(false);
  private loaded = false;

  readonly payments: Observable<Payment[]> = this.payments$.asObservable();
  readonly loading: Observable<boolean> = this.loading$.asObservable();
  readonly stats: Observable<PaymentStats> = this.payments$.pipe(map(computeStats));
  /** Alertes de la cloche : anomalies et paiements échoués, les plus récents d'abord. */
  readonly alerts: Observable<Payment[]> = this.payments$.pipe(
    map((payments) => payments.filter((p) => isAnomaly(p) || p.status === 'failed').slice(0, 6)),
  );

  constructor(
    private api: PaymentService,
    websocket: WebsocketService,
    @Inject(PLATFORM_ID) private platformId: object,
  ) {
    websocket.getMessages().subscribe((update: Payment) => {
      if (update?.id) this.upsert(update);
    });
  }

  load(force = false): void {
    // Pas d'appel API pendant le pré-rendu serveur : les données arrivent dans le navigateur.
    if (!isPlatformBrowser(this.platformId)) return;
    if (this.loaded && !force) return;
    this.loaded = true;
    this.loading$.next(true);
    this.api.getPayments().subscribe({
      next: (rows: Payment[]) => {
        this.payments$.next(rows ?? []);
        this.loading$.next(false);
      },
      error: () => {
        this.loaded = false;
        this.loading$.next(false);
      },
    });
  }

  private upsert(update: Payment): void {
    const rows = [...this.payments$.value];
    const index = rows.findIndex((p) => p.id === update.id);
    if (index >= 0) rows[index] = { ...rows[index], ...update };
    else rows.unshift(update);
    this.payments$.next(rows);
  }
}

// ─── Fonctions d'affichage partagées ──────────────────────────────────

const STATUS: Record<string, { label: string; tone: string }> = {
  success: { label: 'Payé', tone: 'success' },
  pending: { label: 'En attente', tone: 'warning' },
  failed: { label: 'Échoué', tone: 'danger' },
  cancelled: { label: 'Annulé', tone: 'secondary' },
};

const PROVIDERS: Record<string, string> = {
  stripe: 'Carte · Stripe',
  simulator: 'Simulateur',
  mvola: 'MVola',
};

export function statusOf(payment: Payment): { label: string; tone: string } {
  return STATUS[payment?.status] ?? { label: payment?.status || '—', tone: 'secondary' };
}

export function providerLabel(payment: Payment): string {
  // Paiements historiques du monitoring : Stripe Checkout sans champ provider.
  return PROVIDERS[payment?.provider ?? ''] ?? 'Carte · Stripe';
}

export function sourceOf(payment: Payment): string {
  return payment?.source === 'BazarStore' ? 'BazarStore' : 'Monitoring';
}

export function customerName(payment: Payment): string {
  return payment?.customer_name || payment?.user_id || 'Client inconnu';
}

export function isAnomaly(payment: Payment): boolean {
  return String(payment?.prediction || '').startsWith('anomalie');
}

export function formatAmount(amount: number, currency = 'USD'): string {
  if (currency === 'MGA') {
    return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(amount)} Ar`;
  }
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}

function dayKey(date: Date): string {
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

function computeStats(payments: Payment[]): PaymentStats {
  const count = (status: string) => payments.filter((p) => p.status === status).length;
  const paidRows = payments.filter((p) => p.status === 'success');
  const paidMgaRows = paidRows.filter((p) => p.currency === 'MGA');
  const sum = (rows: Payment[]) => rows.reduce((total, p) => total + Number(p.amount || 0), 0);
  const finished = payments.filter((p) => p.status !== 'pending').length;

  const sources = new Map<string, number>();
  for (const p of payments) sources.set(sourceOf(p), (sources.get(sourceOf(p)) ?? 0) + 1);

  // 14 derniers jours, aujourd'hui inclus.
  const days: DayBucket[] = [];
  const index = new Map<string, DayBucket>();
  const today = new Date();
  for (let offset = 13; offset >= 0; offset--) {
    const date = new Date(today.getFullYear(), today.getMonth(), today.getDate() - offset);
    const bucket = {
      label: date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
      count: 0,
      paidMga: 0,
    };
    days.push(bucket);
    index.set(dayKey(date), bucket);
  }
  for (const p of payments) {
    if (!p.created_at) continue;
    const bucket = index.get(dayKey(new Date(p.created_at)));
    if (!bucket) continue;
    bucket.count++;
    if (p.status === 'success' && p.currency === 'MGA') bucket.paidMga += Number(p.amount || 0);
  }

  return {
    total: payments.length,
    paid: paidRows.length,
    pending: count('pending'),
    failed: count('failed'),
    cancelled: count('cancelled'),
    successRate: finished ? Math.round((paidRows.length / finished) * 100) : 0,
    anomalies: payments.filter(isAnomaly).length,
    paidMga: sum(paidMgaRows),
    paidUsd: sum(paidRows.filter((p) => p.currency !== 'MGA')),
    averageMga: paidMgaRows.length ? Math.round(sum(paidMgaRows) / paidMgaRows.length) : 0,
    bySource: [...sources].map(([label, n]) => ({ label, count: n })),
    last14Days: days,
  };
}
