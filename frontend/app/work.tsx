import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Colors } from '@/constants/Colors';
import { IconSymbol } from '@/components/ui/IconSymbol';

// Mock job data for UI demonstration
const mockJobs = [
  {
    id: '1',
    name: 'Henderson House Extension',
    address: '45 Scenic Drive, Henderson',
    status: 'active',
    lastActivity: '2 hours ago',
    questionsCount: 5,
  },
  {
    id: '2', 
    name: 'Auckland CBD Apartment Fit-out',
    address: '123 Queen Street, Auckland',
    status: 'pending',
    lastActivity: '1 day ago',
    questionsCount: 12,
  },
  {
    id: '3',
    name: 'Tauranga Deck Installation',
    address: '67 Marine Parade, Tauranga',
    status: 'complete',
    lastActivity: '3 days ago',
    questionsCount: 8,
  },
];

const statusColors = {
  active: Colors.dark.statusActive,
  pending: Colors.dark.statusPending,
  complete: Colors.dark.statusComplete,
};

export default function WorkScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Add new job button */}
        <TouchableOpacity style={styles.addJobButton}>
          <IconSymbol name="plus" size={20} color={Colors.dark.background} />
          <Text style={styles.addJobText}>New Job</Text>
        </TouchableOpacity>

        {/* Jobs list */}
        <View style={styles.jobsList}>
          {mockJobs.map((job) => (
            <TouchableOpacity key={job.id} style={styles.jobCard}>
              <View style={styles.jobHeader}>
                <Text style={styles.jobName}>{job.name}</Text>
                <View style={[styles.statusBadge, { backgroundColor: statusColors[job.status] }]}>
                  <Text style={styles.statusText}>{job.status}</Text>
                </View>
              </View>
              
              <Text style={styles.jobAddress}>{job.address}</Text>
              
              <View style={styles.jobFooter}>
                <Text style={styles.lastActivity}>Last activity: {job.lastActivity}</Text>
                <View style={styles.questionsCount}>
                  <IconSymbol name="message.fill" size={14} color={Colors.dark.icon} />
                  <Text style={styles.questionsText}>{job.questionsCount}</Text>
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Empty state message */}
        {mockJobs.length === 0 && (
          <View style={styles.emptyState}>
            <IconSymbol name="briefcase.fill" size={48} color={Colors.dark.icon} />
            <Text style={styles.emptyTitle}>No jobs yet</Text>
            <Text style={styles.emptySubtitle}>
              Create your first job to start tracking questions and compliance notes
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.dark.background,
  },
  content: {
    padding: 20,
  },
  addJobButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.dark.tint,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginBottom: 24,
    gap: 8,
  },
  addJobText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.background,
  },
  jobsList: {
    gap: 16,
  },
  jobCard: {
    backgroundColor: Colors.dark.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.dark.border,
  },
  jobHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  jobName: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.dark.text,
    flex: 1,
    marginRight: 12,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.dark.background,
    textTransform: 'uppercase',
  },
  jobAddress: {
    fontSize: 14,
    color: Colors.dark.icon,
    marginBottom: 12,
  },
  jobFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  lastActivity: {
    fontSize: 12,
    color: Colors.dark.placeholder,
  },
  questionsCount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  questionsText: {
    fontSize: 12,
    color: Colors.dark.icon,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.dark.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: Colors.dark.icon,
    textAlign: 'center',
    lineHeight: 20,
  },
});