# app/routes/community.py
# Inside community.py


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Community, CommunityMembership  # adjust import path as needed

community_bp = Blueprint("community_bp", __name__)

@community_bp.route('/communities/<int:community_id>/join', methods=['POST'])
@jwt_required()
def join_community(community_id):
    user_id = get_jwt_identity()  
    community = Community.query.get(community_id)
    if not community:
        return jsonify({'error': 'Community not found'}), 404

    existing_member = CommunityMembership.query.filter_by(
        user_id=user_id, community_id=community_id
    ).first()
    if existing_member:
        return jsonify({'error': 'Already a member'}), 400

    # Create membership
    new_membership = CommunityMembership(user_id=user_id, community_id=community_id)
    db.session.add(new_membership)
    db.session.commit()

    return jsonify({'message': 'Joined community successfully'}), 201
