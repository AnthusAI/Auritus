import './globals.css';
import Header from '../components/Header';
import AuthGuard from '../components/AuthGuard';

export const metadata = {
  title: 'Auritus Operator Console',
  description: 'Monitoring and observability dashboard for Auritus just-in-time TTS.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>
          <AuthGuard>{children}</AuthGuard>
        </main>
      </body>
    </html>
  );
}
