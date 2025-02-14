import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class PaymentService {
  private API_URL = `${environment.apiUrl}/payments`;

  constructor(private http: HttpClient) {}

  // 🔹 Récupérer tous les paiements
  getPayments(): Observable<any> {
    return this.http.get(`${this.API_URL}/recent`);
  }

  // 🔹 Créer une session Stripe Checkout
  createCheckoutSession(userId: string, amount: number): Observable<any> {
    const params = new HttpParams()
      .set('user_id', userId)
      .set('amount', amount.toString());
  
    return this.http.post(`${this.API_URL}/checkout`, null, { params });
  }
}
