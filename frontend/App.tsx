import React from 'react';
import { Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import ChatScreen from './src/screens/ChatScreen';
import LibraryScreen from './src/screens/LibraryScreen';
import ToolsScreen from './src/screens/ToolsScreen';
import { theme } from './src/theme';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerTitle: 'STRYDA.ai',
          headerStyle: {
            backgroundColor: theme.bg,
          },
          headerTitleStyle: {
            fontWeight: 'bold',
            fontSize: 20,
            color: theme.text,
          },
          tabBarActiveTintColor: theme.accent,
          tabBarInactiveTintColor: '#777',
          tabBarStyle: {
            backgroundColor: '#0B0B0B',
            borderTopColor: '#161616',
            borderTopWidth: 1,
            paddingBottom: 8,
            paddingTop: 8,
            height: 60,
          },
          tabBarIcon: ({ color, size }) => {
            const iconMap: Record<string, keyof typeof Ionicons.glyphMap> = {
              Chat: 'chatbubble-ellipses',
              Library: 'library',
              Tools: 'construct'
            };
            const iconName = iconMap[route.name] || 'ellipse';
            return <Ionicons name={iconName} color={color} size={size} />;
          }
        })}
      >
        <Tab.Screen name="Chat" component={ChatScreen} />
        <Tab.Screen name="Library" component={LibraryScreen} />
        <Tab.Screen name="Tools" component={ToolsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
