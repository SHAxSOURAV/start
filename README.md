# Mount Fuji Mobile Application (React Native + Expo Router)

Universal mobile application for iOS, Android, and Web built using **Expo SDK 52**, **Expo Router**, and **TypeScript**, aligned with live best practices from Context7.

---

## 1. Tech Stack & Architectural Patterns

- **Framework**: [Expo SDK 52](https://docs.expo.dev/) (Universal React Native)
- **Routing**: [Expo Router](https://docs.expo.dev/router/introduction/) (File-based navigation with `Stack` and `Tabs`)
- **State Management**: [Zustand](https://zustand-demo.pmnd.rs/) for client state & [TanStack Query v5](https://tanstack.com/query) for server caching
- **Real-Time Client**: `socket.io-client` connected to the Backend Socket.IO ASGI server
- **HTTP Client**: Axios with request/response interceptors for Bearer tokens
- **Type Safety**: TypeScript in strict mode extending `expo/tsconfig.base`

---

## 2. Directory Layout

```
frontend/
├── app.json                # Expo application configuration & plugins
├── tsconfig.json           # Path aliases (@/* -> ./src/*)
├── metro.config.js         # Metro bundler configuration
├── package.json            # Dependencies & start scripts
└── src/
    ├── app/                # Expo Router file-based route hierarchy
    │   ├── _layout.tsx     # Root stack layout & QueryClientProvider
    │   ├── (auth)/         # Unauthenticated route group
    │   │   ├── _layout.tsx
    │   │   ├── login.tsx   # Login screen
    │   │   └── register.tsx
    │   └── (tabs)/         # Authenticated tab navigation
    │       ├── _layout.tsx # Bottom tab bar
    │       ├── index.tsx   # Home feed
    │       ├── chat.tsx    # Real-time chat list
    │       └── profile.tsx # User profile & account management
    ├── components/         # Reusable mobile UI components
    ├── hooks/              # Custom React hooks (useAuth, useSocket)
    ├── services/           # Backend API caller (apiClient)
    ├── socket/             # Socket.IO client instance & event listeners
    └── types/              # DTOs & API response shapes
```

---

## 3. Getting Started

### Prerequisites
- Node.js `>=18`
- npm or pnpm or yarn
- Expo Go app on physical iOS/Android device OR Xcode / Android Studio simulators

### Installation
```bash
cd frontend
npm install
```

### Running the App
```bash
# Start the Metro bundler
npm start

# Run on Android emulator / connected device
npm run android

# Run on iOS simulator (macOS required)
npm run ios

# Run in Web browser
npm run web
```

---

## 4. Environment Variables

Create `.env` inside `frontend/`:
```env
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
EXPO_PUBLIC_SOCKET_URL=http://localhost:8000
```
*(On physical devices, replace `localhost` with your machine's local LAN IP e.g. `192.168.1.X`)*
