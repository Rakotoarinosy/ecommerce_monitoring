import { Component, HostListener, Inject, OnDestroy, OnInit, PLATFORM_ID } from '@angular/core';
import { AsyncPipe, CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { RouterLink, RouterModule, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { PaymentsStore, customerName, formatAmount, isAnomaly } from '../../services/payments-store.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterModule, RouterLink, CommonModule, AsyncPipe, FormsModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent implements OnInit, OnDestroy {
  readonly apiDocsUrl = `${environment.apiUrl}/docs`;
  readonly year = new Date().getFullYear();
  readonly alerts$ = this.store.alerts;
  readonly formatAmount = formatAmount;
  readonly customerName = customerName;
  readonly isAnomaly = isAnomaly;

  sidebarOpen = false;
  alertsOpen = false;
  searchQuery = '';
  apiOnline = true;
  private healthTimer?: ReturnType<typeof setInterval>;

  constructor(
    private router: Router,
    private store: PaymentsStore,
    private http: HttpClient,
    @Inject(PLATFORM_ID) private platformId: object,
  ) {
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.sidebarOpen = false;
        this.alertsOpen = false;
      });
  }

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;
    // Alertes de la cloche, disponibles sur toutes les pages.
    this.store.load();
    this.checkHealth();
    this.healthTimer = setInterval(() => this.checkHealth(), 30_000);
  }

  ngOnDestroy(): void {
    clearInterval(this.healthTimer);
  }

  search(): void {
    const q = this.searchQuery.trim();
    this.router.navigate(['/back-office/transactions'], { queryParams: q ? { q } : {} });
  }

  // Le JS Bootstrap chargé est la v4 (ignore data-bs-toggle) : menu géré ici.
  toggleAlerts(event: Event): void {
    event.stopPropagation();
    this.alertsOpen = !this.alertsOpen;
  }

  @HostListener('document:click', ['$event'])
  closeAlertsOnOutsideClick(event: Event): void {
    if (this.alertsOpen && !(event.target as HTMLElement).closest('.alerts-menu')) {
      this.alertsOpen = false;
    }
  }

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  closeSidebar(): void {
    this.sidebarOpen = false;
  }

  private checkHealth(): void {
    this.http.get(`${environment.apiUrl}/health`).subscribe({
      next: () => (this.apiOnline = true),
      error: () => (this.apiOnline = false),
    });
  }
}
