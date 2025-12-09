using UnityEditor;
using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

#if UNITY_2018_3_OR_NEWER

#endif

public class PrefabRaycastTargetEditor : EditorWindow
{
    [MenuItem("Tools/优化预制体RaycastTarget设置")]
    public static void ShowWindow()
    {
        GetWindow<PrefabRaycastTargetEditor>("RaycastTarget优化");
    }

    private void OnGUI()
    {
        GUILayout.Label("RaycastTarget设置优化工具", EditorStyles.boldLabel);
        
        if (GUILayout.Button("优化当前预制体"))
        {
            OptimizeCurrentPrefab();
        }
    }

    [MenuItem("GameObject/优化RaycastTarget设置", false, 0)]
    private static void OptimizeRaycastTargetMenu()
    {
        OptimizeCurrentPrefab();
    }

    private static void OptimizeCurrentPrefab()
    {
#if UNITY_2018_3_OR_NEWER
        // 检查是否在预制体编辑模式下
        var prefabStage = UnityEditor.SceneManagement.PrefabStageUtility.GetCurrentPrefabStage();
        if (prefabStage == null)
        {
            EditorUtility.DisplayDialog("错误", "请先在预制体编辑模式下打开一个预制体", "确定");
            return;
        }

        var prefabRoot = prefabStage.prefabContentsRoot;
#else
        // 对于旧版本Unity，使用选中对象
        if (Selection.activeGameObject == null)
        {
            EditorUtility.DisplayDialog("错误", "请先选中一个预制体实例", "确定");
            return;
        }
        
        var prefabRoot = Selection.activeGameObject;
#endif

        OptimizePrefab(prefabRoot);
        
        EditorUtility.DisplayDialog("完成", "RaycastTarget优化完成！", "确定");
    }

    private static void OptimizePrefab(GameObject prefabRoot)
    {
        Undo.RecordObject(prefabRoot, "优化RaycastTarget设置");

        bool hasChanges = false;

        // 第一步：找到所有Image和EvonyImage组件，关闭RaycastTarget
        var allImages = prefabRoot.GetComponentsInChildren<Image>(true);
        var evonyImages = new List<MonoBehaviour>();
        
        // 查找所有可能包含EvonyImage组件的对象
        var allBehaviours = prefabRoot.GetComponentsInChildren<MonoBehaviour>(true);
        foreach (var behaviour in allBehaviours)
        {
            if (behaviour != null && behaviour.GetType().Name == "EvonyImage")
            {
                evonyImages.Add(behaviour);
            }
        }

        // 处理普通Image
        foreach (var image in allImages)
        {
            if (image.raycastTarget)
            {
                image.raycastTarget = false;
                hasChanges = true;
                Debug.Log($"已关闭 {GetGameObjectPath(image.gameObject)} 的RaycastTarget", image.gameObject);
            }
        }

        // 处理EvonyImage（通过反射）
        foreach (var evonyImage in evonyImages)
        {
            var raycastTargetProperty = evonyImage.GetType().GetProperty("raycastTarget");
            if (raycastTargetProperty != null)
            {
                var currentValue = (bool)raycastTargetProperty.GetValue(evonyImage);
                if (currentValue)
                {
                    raycastTargetProperty.SetValue(evonyImage, false);
                    hasChanges = true;
                    Debug.Log($"已关闭 {GetGameObjectPath(evonyImage.gameObject)} 的EvonyImage RaycastTarget", evonyImage.gameObject);
                }
            }
        }

        // 第二步：处理所有Button组件
        var allButtons = prefabRoot.GetComponentsInChildren<Button>(true);
        foreach (var button in allButtons)
        {
            if (button.targetGraphic != null)
            {
                // 检查TargetGraphic是否为Image
                var image = button.targetGraphic as Image;
                if (image != null)
                {
                    if (!image.raycastTarget)
                    {
                        image.raycastTarget = true;
                        hasChanges = true;
                        Debug.Log($"已开启 {GetGameObjectPath(image.gameObject)} 的RaycastTarget（Button TargetGraphic）", image.gameObject);
                    }
                    continue;
                }

                // 检查TargetGraphic是否为EvonyImage
                var evonyImage = button.targetGraphic as MonoBehaviour;
                if (evonyImage != null && evonyImage.GetType().Name == "EvonyImage")
                {
                    var raycastTargetProperty = evonyImage.GetType().GetProperty("raycastTarget");
                    if (raycastTargetProperty != null)
                    {
                        var currentValue = (bool)raycastTargetProperty.GetValue(evonyImage);
                        if (!currentValue)
                        {
                            raycastTargetProperty.SetValue(evonyImage, true);
                            hasChanges = true;
                            Debug.Log($"已开启 {GetGameObjectPath(evonyImage.gameObject)} 的EvonyImage RaycastTarget（Button TargetGraphic）", evonyImage.gameObject);
                        }
                    }
                }
            }
        }

        if (hasChanges)
        {
            EditorUtility.SetDirty(prefabRoot);
            PrefabUtility.RecordPrefabInstancePropertyModifications(prefabRoot);
            
            // 保存预制体
            var prefabPath = PrefabUtility.GetPrefabAssetPathOfNearestInstanceRoot(prefabRoot);
            if (!string.IsNullOrEmpty(prefabPath))
            {
                AssetDatabase.SaveAssets();
            }
        }
    }

    private static string GetGameObjectPath(GameObject obj)
    {
        if (obj == null) return "";
        
        string path = "/" + obj.name;
        while (obj.transform.parent != null)
        {
            obj = obj.transform.parent.gameObject;
            path = "/" + obj.name + path;
        }
        return path;
    }
}