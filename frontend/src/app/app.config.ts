import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration, withNoHttpTransferCache } from '@angular/platform-browser';
import { provideHttpClient, withFetch } from '@angular/common/http';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    // Pas de cache de transfert HTTP : les pages pré-rendues au build figeraient
    // les réponses de l'API (paiements, logs…) au moment du déploiement.
    provideClientHydration(withNoHttpTransferCache()),
    provideHttpClient(withFetch()),
  ]
};
