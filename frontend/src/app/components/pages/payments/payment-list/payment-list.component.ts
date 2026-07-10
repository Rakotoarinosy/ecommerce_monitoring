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

  constructor(
    private paymentService: PaymentService,
    private websocketService: WebsocketService
  ) {}

  ngOnInit(): void {
    this.fetchPayments();

    // 🎯 Écouter les mises à jour via WebSocket une seule fois
    this.websocketService.getMessages().subscribe((newPayment: any) => {
      if (newPayment) {
        console.log("💡 Nouveau paiement reçu :", newPayment);
        this.payments.unshift(newPayment); // Ajouter le nouveau paiement en haut de la liste
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
