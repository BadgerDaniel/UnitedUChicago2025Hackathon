import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import AppConnected from './AppConnected.tsx';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppConnected />
  </StrictMode>
);