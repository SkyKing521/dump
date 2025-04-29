def load_rooms(self):
    """Load and display available rooms"""
    try:
        # Clear existing items
        self.rooms_list.clear()
        
        # Get all rooms
        rooms = self.session.query(Room).all()
        
        # Add rooms to list
        for room in rooms:
            # Create item with room name and privacy status
            item = QListWidgetItem()
            if room.is_public:
                item.setText(f"🌐 {room.name}")
            else:
                item.setText(f"🔒 {room.name}")
            item.setData(Qt.ItemDataRole.UserRole, room.id)
            self.rooms_list.addItem(item)
            
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load rooms: {str(e)}")

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
            
        # Check if room already exists
        existing_room = self.session.query(Room).filter(Room.name == name).first()
        if existing_room:
            QMessageBox.critical(self, "Error", "Room with this name already exists")
            return
            
        # Ask if room should be private
        is_private = QMessageBox.question(
            self,
            "Room Privacy",
            "Should this room be private?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes
            
        password = None
        if is_private:
            # Get password for private room
            password, ok = QInputDialog.getText(
                self,
                "Private Room",
                "Enter room password:",
                QLineEdit.EchoMode.Password
            )
            
            if not ok or not password:
                return
                
        # Create room
        room = Room(
            name=name,
            is_public=not is_private,
            password=password
        )
        
        self.session.add(room)
        self.session.commit()
        
        # Refresh room list
        self.load_rooms()
        
        QMessageBox.information(self, "Success", f"Room '{name}' created successfully")
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to create room: {str(e)}") 