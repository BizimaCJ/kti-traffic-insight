import { Link } from 'react-router-dom';
import { Compass } from 'lucide-react';
import { EmptyState } from '../components/ui';
import { useDocumentTitle } from '../lib/hooks';

export default function NotFound() {
  useDocumentTitle('Page not found');
  return (
    <div className="card">
      <EmptyState icon={Compass} title="This page does not exist" action={<Link to="/" className="btn btn-primary">Go to the overview</Link>}>
        The link may be old or mistyped.
      </EmptyState>
    </div>
  );
}
