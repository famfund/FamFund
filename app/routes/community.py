from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import app.firebase as fb  # Import Firebase module
from firebase_admin import auth
from typing import List


# Mock data: Dictionary where keys are community IDs, and values are lists of members
communities = {
    1: ["Alice", "Bob", "Charlie"],
    2: ["David", "Eve", "Frank"],
    3: ["Grace", "Hank", "Ivy"]
}

@router.get("/api/community/members/{community_id}", response_model=List[str])
def get_community_members(community_id: int):
    """
    Retrieve all members of a given community by community_id.
    If the community does not exist, return an empty list.
    """
    return communities.get(community_id, [])

class Community(BaseModel):
    community_name: str
    description: str
    platform_id: str

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
