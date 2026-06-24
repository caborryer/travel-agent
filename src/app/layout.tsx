import type {ReactNode} from 'react';
import {NextIntlClientProvider} from 'next-intl';
import {getLocale, getMessages} from 'next-intl/server';
import {Geist, Geist_Mono} from 'next/font/google';
import type {Metadata} from 'next';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Travel Agent',
  description: 'Tu asistente de viajes low-cost',
};

type Props = {
  children: ReactNode;
};

export default async function RootLayout({children}: Props) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-gradient-to-br from-teal-50 via-white to-emerald-50 dark:from-zinc-950 dark:via-zinc-900 dark:to-emerald-950">
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
