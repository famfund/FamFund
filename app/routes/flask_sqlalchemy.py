from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Blueprint, Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'SUPER_SECRET_KEY'  # Change to something secure in production

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Relationship back to membership records
    memberships = db.relationship('CommunityMembership', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'


class Community(db.Model):
    __tablename__ = 'communities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationship back to membership records
    memberships = db.relationship('CommunityMembership', back_populates='community')

    def __repr__(self):
        return f'<Community {self.name}>'


class CommunityMembership(db.Model):
    """
    This table links Users <--> Communities in a many-to-many relationship.
    It also stores extra data (joined_at, role, etc.) about each membership.
    """
    __tablename__ = 'community_memberships'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    role = db.Column(db.String(50), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='memberships')
    community = db.relationship('Community', back_populates='memberships')

    def __repr__(self):
        return f'<CommunityMembership user_id={self.user_id} community_id={self.community_id}>'


# -----------------------------------------------------
# 3. Create/initialize database (only run once)
#    In production, you'd manage migrations instead.
# -----------------------------------------------------
@app.before_first_request
def create_tables():
    db.create_all()


# -----------------------------------------------------
# 4. Simple routes for demonstration
# -----------------------------------------------------
@app.route('/register', methods=['POST'])
def register():
    """Create a test user (no real auth flow here – just a quick demo)."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(username=username, email=email)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({'message': 'User created', 'access_token': access_token}), 201


@app.route('/communities', methods=['POST'])
@jwt_required()
def create_community():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')

    # Create the community
    community = Community(name=name, description=description)
    db.session.add(community)
    db.session.commit()
    return jsonify({'message': 'Community created', 'community_id': community.id}), 201


@app.route('/communities/<int:community_id>/join', methods=['POST'])
@jwt_required()
def join_community(community_id):
    """Join the specified community (requires JWT token)."""
    user_id = get_jwt_identity()

    community = Community.query.get(community_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404

    existing_membership = CommunityMembership.query.filter_by(
        user_id=user_id,
        community_id=community_id
    ).first()
    if existing_membership:
        return jsonify({'error': 'User is already a member'}), 400

    # Create a new membership
    membership = CommunityMembership(user_id=user_id, community_id=community_id)
    db.session.add(membership)
    db.session.commit()

    return jsonify({'message': 'Successfully joined the community'}), 201


@app.route('/communities/<int:community_id>/members', methods=['GET'])
def list_community_members(community_id):
    """Public endpoint: list all members in a community."""
    community = Community.query.get(community_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404

    members_data = []
    for membership in community.memberships:
        user_obj = membership.user
        members_data.append({
            'user_id': user_obj.id,
            'username': user_obj.username,
            'role': membership.role,
            'joined_at': membership.joined_at.isoformat()
        })

    return jsonify({
        'community_id': community.id,
        'community_name': community.name,
        'members': members_data
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
