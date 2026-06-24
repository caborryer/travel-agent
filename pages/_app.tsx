import type {AppProps} from 'next/app';
import {Geist, Geist_Mono} from 'next/font/google';
import {LocaleProvider} from '@/components/i18n/LocaleProvider';
import '@/app/globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export default function App({Component, pageProps}: AppProps) {
  return (
    <div
      className={`${geistSans.variable} ${geistMono.variable} min-h-full flex flex-col antialiased bg-gradient-to-br from-teal-50 via-white to-emerald-50 dark:from-zinc-950 dark:via-zinc-900 dark:to-emerald-950`}
    >
      <LocaleProvider>
        <Component {...pageProps} />
      </LocaleProvider>
    </div>
  );
}
