import dynamic from 'next/dynamic';

const HomePage = dynamic(() => import('@/app/HomePage'), {ssr: false});

export default function IndexPage() {
  return <HomePage />;
}
