import { Component, OnInit } from '@angular/core';
import { PaymentService } from '../../../services/payement.service';
import { WebsocketService } from '../../../services/websocket.service';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-payment-list',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  templateUrl: './payment-list.component.html',
  styleUrl: './payment-list.component.scss'
})
export class PaymentListComponent implements OnInit {
  payments: any[] = [];

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
    });
  }

  // 🔹 Déclencher le paiement
  initiatePayment(): void {
    const userId = "123testa"; // Remplacez par l'ID utilisateur réel
    const amount = 55; // Remplacez par le montant réel

    this.paymentService.createCheckoutSession(userId, amount).subscribe(
      (response) => {
        console.log('Réponse du serveur:', response); // Affiche la valeur retournée
        window.location.href = response.checkout_url
      },
      (error) => {
        console.error('Erreur lors de la requête:', error);
      }
    );
    
  }
}
