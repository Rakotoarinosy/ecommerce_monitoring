import { Component } from '@angular/core';
import { WebsocketService } from '../../../services/websocket.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss'
})
export class LogsComponent {

  logs: any[] = [];

  constructor(private websocketService: WebsocketService) {}

  ngOnInit(): void {
    this.websocketService.getLogs().subscribe((data) => {
      if (data.logs) {
        this.logs = data.logs; // ✅ Met à jour la liste des logs
      }
    });
  }
}
