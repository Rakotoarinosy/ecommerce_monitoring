import { Routes } from '@angular/router';
import { PaymentListComponent } from './components/payments/payment-list/payment-list.component';

export const routes: Routes = [
    {
        path: 'list-payments',
        component: PaymentListComponent
    }
];
