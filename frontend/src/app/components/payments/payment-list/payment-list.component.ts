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

    // 🎯 Mettre à jour en temps réel
    this.websocketService.getMessages().subscribe((message) => {
      console.log("💡 Nouveau paiement reçu :", message);
      if (message) {
        this.payments.unshift(message);
      }
    });
  }

  fetchPayments(): void {
    this.paymentService.getPayments().subscribe((data) => {
      this.payments = data;
    });
  }
}
