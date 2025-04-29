import asyncio
import json

def load_rooms(self):
    """Load and display available rooms"""
    try:
        # Clear existing items
        self.rooms_list.clear()
        
        # Get rooms from database
        rooms = self.session.query(Room).all()
        
        # Add rooms to list
        for room in rooms:
            item = QListWidgetItem()
            if room.is_public:
                item.setText(f"🌐 {room.name}")
            else:
                item.setText(f"🔒 {room.name}")
            item.setData(Qt.ItemDataRole.UserRole, room.id)
            self.rooms_list.addItem(item)
            
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load rooms: {str(e)}")

def handle_room_list(self, data):
    """Handle room list update from server"""
    try:
        # Clear existing items
        self.rooms_list.clear()
        
        # Add rooms to list
        for room in data['rooms']:
            item = QListWidgetItem()
            if room['is_public']:
                item.setText(f"🌐 {room['name']}")
            else:
                item.setText(f"🔒 {room['name']}")
            item.setData(Qt.ItemDataRole.UserRole, room['id'])
            self.rooms_list.addItem(item)
            
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to update room list: {str(e)}")

def join_room(self):
    """Join selected room"""
    try:
        # Get selected room
        selected_items = self.rooms_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a room to join")
            return
            
        room_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        room = self.session.query(Room).filter(Room.id == room_id).first()
        
        if not room:
            QMessageBox.critical(self, "Error", "Room not found")
            return
            
        # Check if room is private
        if not room.is_public:
            # Ask for password
            password, ok = QInputDialog.getText(
                self,
                "Private Room",
                "Enter room password:",
                QLineEdit.EchoMode.Password
            )
            
            if not ok:
                return
                
            if password != room.password:
                QMessageBox.critical(self, "Error", "Incorrect password")
                return
                
        # Join room
        self.current_room = room
        self.status_label.setText(f"Joined room: {room.name}")
        self.join_button.setEnabled(False)
        self.leave_button.setEnabled(True)
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to join room: {str(e)}")

def create_room(self):
    """Create a new room"""
    try:
        # Get room name
        name, ok = QInputDialog.getText(
            self,
            "Create Room",
            "Enter room name:"
        )
        
        if not ok or not name:
            return
            
        # Ask if room should be private
        is_private = QMessageBox.question(
            self,
            "Room Privacy",
            "Should this room be private?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
        
        # Send create room request to server
        if self.webrtc_client and self.webrtc_client.websocket:
            asyncio.run(self.webrtc_client.websocket.send(json.dumps({
                'type': 'create-room',
                'name': name,
                'is_public': not is_private,
                'user_id': self.current_user.id
            })))
        else:
            QMessageBox.critical(self, "Error", "Not connected to server")
            
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to create room: {str(e)}") 