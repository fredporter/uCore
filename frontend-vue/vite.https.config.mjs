// Trusted local HTTPS for the Safari standalone web app.
//
// Safari's Add to Dock refuses plain-HTTP localhost, so the dev app is served
// once over a trusted local certificate. Started by
// scripts/enable-engineering-https.sh, which supplies the certificate paths.
// The documented runtime remains http://localhost:5175.
import base from './vite.config';

const config = Array.isArray(base) ? base[0] : base;

const cert = process.env.UCORE_HTTPS_CERT;
const key = process.env.UCORE_HTTPS_KEY;

if (!cert || !key) {
  throw new Error(
    'UCORE_HTTPS_CERT and UCORE_HTTPS_KEY are required. ' +
      'Run scripts/enable-engineering-https.sh start instead of calling Vite directly.',
  );
}

export default {
  ...config,
  server: {
    ...(config.server ?? {}),
    host: 'localhost',
    port: Number(process.env.UCORE_HTTPS_PORT ?? 5176),
    strictPort: true,
    https: { cert, key },
  },
};
