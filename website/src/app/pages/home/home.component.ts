import { Component } from '@angular/core';

@Component({
  selector: 'app-home',
  standalone: true,
  template: `
    <div class="home">
      <h1>Welcome!</h1>
      <p>
        I'm a System Developer based in Stockholm, Sweden, working at Uppsala Monitoring Centre.
        This site is intended to be a playground for me to mess around with various web related things, as
        well as teaching myself a bit about cloud infrastructure.
        I also use it to host an occasional blog, as and when I have some interesting stuff to write about.
      </p>
      <p>
        You can see all the source of this website on
        <a href="https://github.com/jimbarrett27/website" target="_blank" rel="noopener noreferrer">GitHub</a>.
      </p>
    </div>
  `,
  styles: [`
    .home {
      max-width: 720px;
      margin: 0 auto;
      padding: 2rem 1rem;
    }

    h1 {
      margin-bottom: 1.5rem;
    }

    p {
      margin-bottom: 1rem;
      line-height: 1.8;
    }

    a {
      color: #0f1219;
    }
  `]
})
export class HomeComponent {}
