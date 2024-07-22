# routes/__init__.py
from .auth_routes import auth_ns
from .home_routes import home_ns
from .registration_routes import registration_ns
from .subscription_routes import subscription_ns
from .contact_routes import contact_ns
from .blog_routes import blog_ns
from .feedback_blog_routes import feedback_ns
from .userinfo_routes import user_ns
from .invoice_routes import invoice_ns
from .chat_routes import chat_ns

def initialize_routes(api, app, mail):
    api.add_namespace(auth_ns, path='/api/auth')
    auth_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(home_ns, path='/api/home')
    home_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(registration_ns, path='/api/registration')
    registration_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(subscription_ns, path='/api')
    subscription_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(contact_ns, path='/api')
    contact_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(blog_ns, path='/api')
    blog_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(feedback_ns, path='/api')
    feedback_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(user_ns, path='/api')
    user_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(invoice_ns, path='/api')
    invoice_ns.context = {'app': app, 'mail': mail}

    api.add_namespace(chat_ns, path='/api')
    chat_ns.context = {'app': app, 'mail': mail}
