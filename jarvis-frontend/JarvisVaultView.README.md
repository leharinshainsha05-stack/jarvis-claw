# JarvisVaultView

`src/JarvisVaultView.jsx` is a standalone React view and is not wired into the existing vanilla JavaScript app.

## Render

The host React app must provide React, React DOM, Tailwind CSS, and `lucide-react`, and its Tailwind source scan must include `src/JarvisVaultView.jsx`.

```jsx
import JarvisVaultView from './src/JarvisVaultView.jsx';

export function App() {
  return <JarvisVaultView />;
}
```

Those packages are not installed in this workspace. No packages were added.

## Demo And Backend Boundary

Demo-only: balances, activity history, service-status labels, form validation, and add/spend/allocate updates held in React state for the current page session. Integer paise calculations live in `src/vault-finance.js`. No browser storage or real payment action is used.

Backend required: persisted balances and transactions, authoritative spending/allocation decisions, real financial rules, account authorization, and confirmed SQLite/Personal Brain/backend service status. No endpoint or WebSocket message protocol is assumed here. Replace the local action handler only after the backend contract is verified; enforce every financial rule on the backend.