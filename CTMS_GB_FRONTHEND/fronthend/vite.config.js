import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: "PTMS",
        short_name: "PTMS",
        start_url: "/",
        display: "standalone",
        theme_color: "#000000",
        background_color: "#ffffff",
        icons: [
          {
            src: "/icons/car.png",
            sizes: "192x192",
            type: "image/png"
          },
          {
            src: "/icons/coaster.png",
            sizes: "512x512",
            type: "image/png"
          },
          {
            src: "/icons/coaster.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable"
          }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.destination === 'document',
            handler: 'NetworkFirst'
          }
        ]
      }
    })
  ],
  server: {
    port: 5173
  }
})
