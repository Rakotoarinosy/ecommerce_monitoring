import { Component } from '@angular/core';
import { RouterLink, RouterModule } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterModule, RouterLink],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  heroImageUrl : any = 'assets/img/undraw_rocket.svg';
  profile: any = "assets/img/undraw_profile.svg";
  image_eo : any = 'assets/img/EO.png';

}
