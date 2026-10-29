import { View, Text, StyleSheet, FlatList } from "react-native";
import { MessageSquare } from "lucide-react-native";

export default function ChatScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.emptyContainer}>
        <MessageSquare size={48} color="#94a3b8" />
        <Text style={styles.emptyTitle}>No Active Conversations</Text>
        <Text style={styles.emptyText}>
          Start a real-time conversation. Messages are persisted in MongoDB via Socket.IO.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  emptyContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#0f172a",
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: "#64748b",
    textAlign: "center",
    marginTop: 8,
    lineHeight: 20,
  },
});

