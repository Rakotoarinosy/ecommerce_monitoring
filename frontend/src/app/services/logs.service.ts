import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface LogLine {
  level: string;
  message: string;
  timestamp: string;
}

export interface LogHistoryPage {
  total: number;
  logs: LogLine[];
}

@Injectable({
  providedIn: 'root'
})
export class LogsService {
  private readonly API_URL = `${environment.apiUrl}/logs`;

  constructor(private http: HttpClient) {}

  /** Logs archivés dans MongoDB (toutes les 5 minutes), du plus récent au plus ancien. */
  getHistory(options: { level?: string; q?: string; skip?: number; limit?: number }): Observable<LogHistoryPage> {
    let params = new HttpParams()
      .set('skip', String(options.skip ?? 0))
      .set('limit', String(options.limit ?? 50));
    if (options.level) params = params.set('level', options.level);
    if (options.q) params = params.set('q', options.q);
    return this.http.get<LogHistoryPage>(`${this.API_URL}/history`, { params });
  }
}
