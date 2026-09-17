import os
# Help detect serverless early
if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    os.environ.setdefault('VERCEL', '1')

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
