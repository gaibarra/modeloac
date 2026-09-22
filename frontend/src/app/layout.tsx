import type { Metadata } from 'next';
import './institutional.css';
import './globals.css';
export const metadata: Metadata = {title:'Modelo AC · Escuela Modelo',description:'Gestión institucional de climatización, inventario y mantenimiento.'};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="es"><body>{children}</body></html>;}
