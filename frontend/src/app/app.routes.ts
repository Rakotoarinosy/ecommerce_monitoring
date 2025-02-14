import { Routes } from '@angular/router';

export const routes: Routes = [
    {
      path: 'back-office',
      loadComponent: () => import('./components/sidebar/sidebar.component').then(m => m.SidebarComponent),
      children: [
        {
          path: 'list-payments',
          loadComponent: () => import('./components/layout/layout.component').then(m => m.LayoutComponent),
          children: [
            {
              path: '',
              loadComponent: () => import('./components/pages/payments/payment-list/payment-list.component').then(m => m.PaymentListComponent),
            },
          ],
        },
        {
            path: 'dashboard',
            loadComponent: () => import('./components/pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
        },
        {
            path: 'logs',
            loadComponent: () => import('./components/pages/logs/logs.component').then(m => m.LogsComponent),
        },
        { path: '', redirectTo: 'list-payments', pathMatch: 'full' },
      ],
    },
    // Redirection par défaut
    {
      path: '',
      redirectTo: 'back-office',
      pathMatch: 'full',
    },
    // Route wildcard pour capturer les erreurs 404
    {
      path: '**',
      redirectTo: 'back-office',
    },
];
