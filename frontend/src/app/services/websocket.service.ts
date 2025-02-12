import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Observable } from 'rxjs';
import { WebSocketSubject } from 'rxjs/webSocket';

@Injectable({
  providedIn: 'root',
})
export class WebsocketService {
  private socket$: WebSocketSubject<any> | null = null;

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {
    if (isPlatformBrowser(this.platformId)) {
      // ✅ WebSocket activé uniquement côté client
      this.socket$ = new WebSocketSubject('ws://localhost:8000/ws/payments');
    }
  }

  // ✅ Vérifie si WebSocket est initialisé avant d'utiliser getMessages()
  getMessages(): Observable<any> {
    if (!this.socket$) {
      console.warn('WebSocket non disponible côté serveur');
      return new Observable(); // Retourne un Observable vide en SSR
    }
    return this.socket$.asObservable();
  }
}
