/** Las redes del canal. El launcher las muestra en Créditos y la web en el pie. */
export type Social = {
  name: string;
  handle: string;
  url: string;
  color: string;
  /** Trazo del logo, en un lienzo de 24 por 24. */
  path: string;
};

export const socials: Social[] = [
  {
    name: 'Kick',
    handle: 'elsobrinodepepe',
    url: 'https://kick.com/elsobrinodepepe',
    color: '#53FC18',
    path: 'M3 3h6v4h2V5h2V3h6v6h-2v2h-2v2h2v2h2v6h-6v-2h-2v-2H9v4H3V3Z',
  },
  {
    name: 'YouTube',
    handle: 'elsobrinodepepe',
    url: 'https://www.youtube.com/@elsobrinodepepe',
    color: '#FF0033',
    path:
      'M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1c.5-1.9.5-5.8.5-5.8s0-3.9-.5-5.8ZM9.6 15.6V8.4l6.3 3.6-6.3 3.6Z',
  },
  {
    name: 'Instagram',
    handle: 'elsobrinodepepe',
    url: 'https://www.instagram.com/elsobrinodepepe/',
    color: '#E1306C',
    path:
      'M12 2.2c3.2 0 3.6 0 4.9.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1 .4 2.2.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c0 1.2-.2 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.2-1 .4-2.2.4-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-1.2 0-1.8-.2-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.2-.4-.4-1-.4-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.9c0-1.2.2-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.2 1-.4 2.2-.4 1.3-.1 1.7-.1 4.8-.1Zm0 3.1A6.7 6.7 0 1 0 18.7 12 6.7 6.7 0 0 0 12 5.3Zm0 11A4.3 4.3 0 1 1 16.3 12 4.3 4.3 0 0 1 12 16.3Zm6.9-11.2a1.6 1.6 0 1 1-1.6-1.6 1.6 1.6 0 0 1 1.6 1.6Z',
  },
  {
    name: 'TikTok',
    handle: 'sobrinodepepe',
    url: 'https://www.tiktok.com/@sobrinodepepe',
    color: '#25F4EE',
    path:
      'M16.6 5.8a4.8 4.8 0 0 1-1.2-3.2h-3.3v13.1a2.9 2.9 0 1 1-2-2.8V9.5a6.2 6.2 0 1 0 5.3 6.1V9.1a8 8 0 0 0 4.7 1.5V7.3a4.8 4.8 0 0 1-3.5-1.5Z',
  },
];
