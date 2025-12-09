using UnityEngine;
using UnityEditor;
using System;
using System.Collections.Generic;
using System.IO;

public class EditorToolsContainer : EditorWindow
{
    private enum ToolType
    {
        PrefabManager,
        TextPolisher,
        AIDailyReport
    }

    private ToolType selectedTool = ToolType.PrefabManager;
    private Vector2 scrollPosition;

    // 使用字典存储工具实例，便于统一管理
    private Dictionary<ToolType, EditorWindow> tools = new Dictionary<ToolType, EditorWindow>();

    [MenuItem("Tools/ws_ToolsContainer")]
    public static void ShowWindow()
    {
        GetWindow<EditorToolsContainer>("开发工具集");
    }

    private void OnEnable()
    {
        LoadPreferences();
        InitializeTools();
    }

    private void InitializeTools()
    {
        // 统一初始化所有工具
        tools[ToolType.PrefabManager] = CreateInstance<PrefabManagerEditor>();
        tools[ToolType.AIDailyReport] = CreateInstance<AIDailyReport>();
        tools[ToolType.TextPolisher] = CreateInstance<TextPolisher>();

        // 统一设置隐藏状态
        foreach (var tool in tools.Values)
        {
            tool.hideFlags = HideFlags.HideAndDontSave;
        }
    }

    private void OnDisable()
    {
        SavePreferences();
        CleanupTools();
    }

    private void CleanupTools()
    {
        // 统一清理工具实例
        foreach (var tool in tools.Values)
        {
            if (tool != null)
            {
                DestroyImmediate(tool);
            }
        }
        tools.Clear();
    }

    private void LoadPreferences()
    {
        selectedTool = (ToolType)EditorPrefs.GetInt("EditorToolsContainer_SelectedTool", (int)ToolType.PrefabManager);
    }

    private void SavePreferences()
    {
        EditorPrefs.SetInt("EditorToolsContainer_SelectedTool", (int)selectedTool);
    }

    private void OnGUI()
    {
        DrawToolSelection();

        EditorGUILayout.Space();
        EditorGUILayout.LabelField("", GUI.skin.horizontalSlider);
        EditorGUILayout.Space();

        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
        {
            DrawSelectedToolContent();
        }
        EditorGUILayout.EndScrollView();
    }

    private void DrawToolSelection()
    {
        GUILayout.BeginHorizontal();
        {
            GUILayout.FlexibleSpace();

            // 使用循环创建工具选择按钮
            foreach (ToolType toolType in Enum.GetValues(typeof(ToolType)))
            {
                DrawToolSelectionButton(toolType);
            }

            GUILayout.FlexibleSpace();
        }
        GUILayout.EndHorizontal();
    }

    private void DrawToolSelectionButton(ToolType toolType)
    {
        string buttonText = GetToolDisplayName(toolType);
        bool isSelected = selectedTool == toolType;

        if (GUILayout.Toggle(isSelected, buttonText, "Button", GUILayout.Width(80), GUILayout.Height(25)))
        {
            if (!isSelected)
            {
                selectedTool = toolType;
                SavePreferences();
            }
        }
    }

    private string GetToolDisplayName(ToolType toolType)
    {
        switch (toolType)
        {
            case ToolType.PrefabManager: return "预制体管理";
            case ToolType.TextPolisher: return "文本润色";
            case ToolType.AIDailyReport: return "日报周报";
            default: return toolType.ToString();
        }
    }

    private void DrawSelectedToolContent()
    {
        if (!tools.ContainsKey(selectedTool) || tools[selectedTool] == null)
        {
            EditorGUILayout.HelpBox($"{GetToolDisplayName(selectedTool)}加载失败", MessageType.Error);
            return;
        }

        DrawToolContent(tools[selectedTool], GetToolDisplayName(selectedTool));
    }

    private void DrawToolContent(EditorWindow tool, string toolName)
    {
        try
        {
            // 保存原始位置
            var originalPosition = tool.position;

            // 设置临时位置和大小
            tool.position = new Rect(0, 0, position.width, position.height);

            // 调用工具的GUI绘制方法
            if (tool is PrefabManagerEditor prefabManager)
            {
                prefabManager.CallOnGUI();
            }
            else if (tool is AIDailyReport aiDailyReport)
            {
                aiDailyReport.CallOnGUI();
            }
            else if (tool is TextPolisher textPolisher)
            {
                textPolisher.CallOnGUI();
            }

            // 恢复原始位置
            tool.position = originalPosition;
        }
        catch (Exception e)
        {
            EditorGUILayout.HelpBox($"绘制{toolName}时出错: {e.Message}", MessageType.Error);
        }
    }
}