import './globals.css';
import Header from '../components/Header';

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
        <main>{children}</main>
      </body>
    </html>
  );
}
