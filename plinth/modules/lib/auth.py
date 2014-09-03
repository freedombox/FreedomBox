from django.contrib.auth.models import Group, User


def add_user(username, passphrase, name='', email='', expert=False):
    """Add a new user with specified username and passphrase"""
    if not username:
        return 'Must specify a username!'

    if not passphrase:
        return 'Must specify a passphrase!'

    user = User.objects.create_user(username, email=email,
                                    password=passphrase)
    user.first_name = name
    user.save()

    if expert:
        user.groups.add(get_or_create_group('Expert'))


def get_or_create_group(name):
    """Return an existing or newly created group with given name"""
    try:
        group = Group.objects.get(name__exact=name)
    except Group.DoesNotExist:
        group = Group(name=name)
        group.save()

    return group
