import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { PaymentService } from '../../../../services/payement.service';
import { WebsocketService } from '../../../../services/websocket.service';

declare var $: any;

@Component({
  selector: 'app-payment-list',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  templateUrl: './payment-list.component.html',
  styleUrl: './payment-list.component.scss'
})
export class PaymentListComponent implements OnInit {
  payments: any[] = [];
  loading = false;

  private static readonly STATUS = {
    success: { label: 'Payé', tone: 'success' },
    pending: { label: 'En attente', tone: 'warning' },
    failed: { label: 'Échoué', tone: 'danger' },
    cancelled: { label: 'Annulé', tone: 'secondary' },
  } as Record<string, { label: string; tone: string }>;

  private static readonly PROVIDERS: Record<string, string> = {
    stripe: 'Carte · Stripe',
    simulator: 'Simulateur',
    mvola: 'MVola',
  };

  formatAmount(payment: any): string {
    const amount = Number(payment?.amount || 0);
    if ((payment?.currency || 'USD') === 'MGA') {
      return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(amount)} Ar`;
    }
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: payment?.currency || 'USD' }).format(amount);
  }

  status(payment: any): { label: string; tone: string } {
    return PaymentListComponent.STATUS[payment?.status] ?? { label: payment?.status || '—', tone: 'secondary' };
  }

  providerLabel(payment: any): string {
    // Paiements historiques du monitoring : Stripe Checkout sans champ provider.
    return PaymentListComponent.PROVIDERS[payment?.provider] ?? 'Carte · Stripe';
  }

  customerName(payment: any): string {
    return payment?.customer_name || payment?.user_id || 'Client inconnu';
  }

  initials(payment: any): string {
    const parts = this.customerName(payment).split(/\s+/).filter((part) => /[A-Za-zÀ-ÿ]/.test(part));
    return (parts.slice(0, 2).map((part) => part[0]).join('') || '#').toUpperCase();
  }

  /** Paiement venu d'un projet branché sur la passerelle (BazarStore ou autre). */
  isFromShop(payment: any): boolean {
    return !!payment?.source && payment.source !== 'Monitoring';
  }

  isAnomaly(payment: any): boolean {
    return String(payment?.prediction || '').startsWith('anomalie');
  }

  shortId(payment: any): string {
    const id = String(payment?.id || '');
    return id.length > 14 ? `${id.slice(0, 12)}…` : id;
  }

  constructor(
    private paymentService: PaymentService,
    private websocketService: WebsocketService
  ) {}

  ngOnInit(): void {
    this.fetchPayments();

    // 🎯 Écouter les mises à jour via WebSocket une seule fois
    this.websocketService.getMessages().subscribe((newPayment: any) => {
      if (newPayment) {
        // Une intention passe pending → payé : on remplace sa ligne au lieu d'en ajouter une.
        const index = newPayment.id ? this.payments.findIndex((p) => p.id === newPayment.id) : -1;
        if (index >= 0) this.payments[index] = { ...this.payments[index], ...newPayment };
        else this.payments.unshift(newPayment);
      }
    });
  }

  fetchPayments(): void {
    this.paymentService.getPayments().subscribe((data) => {
      this.payments = data;


      setTimeout(() => {
        const table = $('#paymentsTable');
        if ($.fn.DataTable.isDataTable('#paymentsTable')) {
          table.DataTable().destroy();
        }
        table.DataTable({
          order: [],
        });
      }, 0);
    });
  }

  // 🔹 Déclencher le paiement
  initiatePayment(): void {
    this.loading = true;
    const userId = "123"; // Remplacez par l'ID utilisateur réel
    const amount = 35
    this.paymentService.createCheckoutSession(userId, amount).subscribe(
      (response) => {
        console.log('Réponse du serveur:', response); // Affiche la valeur retournée
        window.location.href = response.checkout_url
      },
      (error) => {
        console.error('Erreur lors de la requête:', error);
      },    
      () => {
        this.loading = false;
      }
    );
    
  }
}
