import { View, Text, StyleSheet, ScrollView } from "react-native";

export default function HomeScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome to Mount Fuji</Text>
        <Text style={styles.sub}>High-Performance Mobile Client</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Real-time Connectivity</Text>
        <Text style={styles.cardBody}>
          Connected via WebSockets (Socket.IO) and asynchronous Beanie ODM endpoints.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Cloud Native Architecture</Text>
        <Text style={styles.cardBody}>
          Built on Expo Router SDK 52 with file-based routing, TanStack Query, and TypeScript.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
    padding: 16,
  },
  header: {
    marginVertical: 16,
  },
  greeting: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#0f172a",
  },
  sub: {
    fontSize: 14,
    color: "#64748b",
    marginTop: 4,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#0f172a",
    marginBottom: 8,
  },
  cardBody: {
    fontSize: 14,
    color: "#475569",
    lineHeight: 20,
  },
});

