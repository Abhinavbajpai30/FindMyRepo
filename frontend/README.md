# FindMy Repo

A modern web application for discovering open source repositories to contribute to based on your skills, interests, and availability.

## Features

- AI-powered repository recommendations
- Advanced search and filtering capabilities
- Personalized discovery based on user preferences
- Beautiful, responsive UI with dark theme
- Tetris-style loading animations
- Real-time search with animated backgrounds

## Getting Started

### Prerequisites

- Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Installation

```sh
# Step 1: Clone the repository
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory
cd FindMyRepo/frontend

# Step 3: Install the necessary dependencies
npm i

# Step 4: Start the development server
npm run dev
```

## Technologies Used

This project is built with:

- **Vite** - Fast build tool and development server
- **TypeScript** - Type-safe JavaScript
- **React** - Modern UI library
- **shadcn-ui** - Beautiful, accessible UI components
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful & consistent icon toolkit

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn-ui components
│   ├── Navbar.tsx      # Navigation component
│   ├── RepoCard.tsx    # Repository card component
│   └── ...
├── pages/              # Page components
│   ├── Home.tsx        # Landing page
│   ├── SearchResults.tsx # Search results page
│   ├── HiddenGems.tsx  # Hidden gems page
│   └── ...
├── contexts/           # React contexts
├── hooks/              # Custom React hooks
└── lib/                # Utility functions
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.