import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <main className="container margin-vert--xl">
        <h1>{siteConfig.title}</h1>
        <p>{siteConfig.tagline}</p>
        <Link className="button button--primary" to="/intro">
          Open User Guide
        </Link>
      </main>
    </Layout>
  );
}
