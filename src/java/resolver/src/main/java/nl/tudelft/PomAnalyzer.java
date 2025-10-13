package nl.tudelft;

import com.google.gson.Gson;
import java.io.*;
import java.util.*;
import org.apache.maven.model.*;
import org.apache.maven.model.Model;
import org.apache.maven.model.building.*;
import org.apache.maven.model.building.DefaultModelBuilderFactory;
import org.apache.maven.model.building.DefaultModelBuildingRequest;
import org.apache.maven.model.building.ModelBuildingException;
import org.apache.maven.model.building.ModelBuildingRequest;

public class PomAnalyzer {
  static HashMap<String, Set<String>> reposPerPlugin;
  static HashSet<String> repositoriesSet;

  public static void main(String[] args) throws IOException {
    if (args.length < 1
        || (!args[0].equals("linux")
            && !args[0].equals("windows"))) { // Adjust the number of required arguments
      System.err.println("Usage: java Main <os:linux/windows>");
      System.exit(1); // Exit with an error code
    }

    String basePath = "../../output/java"; // Specify your base directory here
    File baseDir = new File(basePath);
    reposPerPlugin = new HashMap<>();
    repositoriesSet = new HashSet<>();
    int count = 0;

    for (File subDirectory : baseDir.listFiles(File::isDirectory)) {
      File[] repositories = subDirectory.listFiles(File::isDirectory);
      for (File repositoryFile : repositories) {
        String repository = getString(args, repositoryFile);
        System.out.println(count++ + " (" + repositories.length + "): " + repository);
        if (searchForPom(repositoryFile, repository)) {
          repositoriesSet.add(repository);
        }
      }
    }
    Map<String, Set<String>> sortedMap = sortByValueLength();

    // Printing the sorted map
    System.out.println("\nPlugins:");
    sortedMap.forEach(
        (key, value) ->
            System.out.println(key + " [" + value.size() + "/" + repositoriesSet.size() + "]"));

    Map<String, List<String>> reversedMap = new HashMap<>();

    for (Map.Entry<String, Set<String>> entry : reposPerPlugin.entrySet()) {
      String x = entry.getKey();
      Set<String> yList = entry.getValue();

      for (String y : yList) {
        // Add x to the list of x's for this y
        reversedMap.computeIfAbsent(y, k -> new ArrayList<>()).add(x);
      }
    }

    for (String repository : repositoriesSet) {
      if (!reversedMap.containsKey(repository)) {
        reversedMap.put(repository, new ArrayList<>());
      }
    }

    // Convert map to JSON
    Gson gson = new Gson();
    String json = gson.toJson(reversedMap);

    // Write JSON to a file
    try (FileWriter file = new FileWriter("../../data/plugins.json")) {
      file.write(json);
    }
  }

  private static String getString(String[] args, File repositoryFile) {
    String repositoryString = repositoryFile.getAbsolutePath();
    String repository;
    if (args[0].equals("linux")) {
      int startIndex = repositoryString.lastIndexOf("/", repositoryString.lastIndexOf("/") - 1) + 1;
      repository = repositoryString.substring(startIndex);
    } else {
      int startIndex =
          repositoryString.lastIndexOf("\\", repositoryString.lastIndexOf("\\") - 1) + 1;
      repository = repositoryString.substring(startIndex).replace("\\", "/");
    }
    return repository;
  }

  public static Map<String, Set<String>> sortByValueLength() {
    // Create a list of map entries
    List<Map.Entry<String, Set<String>>> entries = new ArrayList<>(reposPerPlugin.entrySet());

    // Sort the list based on the length of the lists (values)
    entries.sort(
        Comparator.comparingInt((Map.Entry<String, Set<String>> e) -> e.getValue().size())
            .reversed());

    // Create a LinkedHashMap to preserve the sorted order
    Map<String, Set<String>> sortedMap = new LinkedHashMap<>();
    for (Map.Entry<String, Set<String>> entry : entries) {
      sortedMap.put(entry.getKey(), entry.getValue());
    }

    return sortedMap;
  }

  public static boolean searchForPom(File directory, String repository) {
    boolean found = false;

    if (!directory.isDirectory()) {
      return found;
    }
    File[] subDirectories = directory.listFiles(File::isDirectory);
    File pomFile = new File(directory, "pom.xml");

    var model = buildEffectiveModel(pomFile);
    if (pomFile.exists() && model != null) {
      found = true;
      analyzePom(pomFile, repository);
    }
    assert subDirectories != null;
    for (File subDirectory : subDirectories) {
      try {
        found = found || searchForPom(subDirectory, repository);
      } catch (Exception e) {
        System.out.println(e.getMessage());
      }
    }
    return found;
  }

  public static void analyzePom(File pomFile, String repository) {
    Model effectivePom = buildEffectiveModel(pomFile);
    if (effectivePom == null) return;
    Build build = effectivePom.getBuild();
    List<Plugin> plugins = build.getPlugins();
    plugins.addAll(build.getPluginManagement().getPlugins());
    for (Plugin plugin : plugins) {
      reposPerPlugin
          .computeIfAbsent(plugin.getGroupId() + ":" + plugin.getArtifactId(), k -> new HashSet<>())
          .add(repository);
    }
  }

  public static Model buildEffectiveModel(File pom) {
    File file =
        new File("resolver/effectivePoms/" + pom.toPath().subpath(3, pom.toPath().getNameCount()));
    boolean publish = true;
    if (file.exists()) {
      SerializableModel model = null;
      try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(file))) {
        model = (SerializableModel) ois.readObject();
      } catch (IOException | ClassNotFoundException e) {
        System.out.println(e.getMessage());
      }
      if (model == null) {
        return null;
      }
      return model.model;
    } else {
      if (file.getParentFile() != null) { // Check if the file has a parent directory
        file.getParentFile().mkdirs(); // Create parent directories if needed
      }
      Model result = null;
      try {
        DefaultModelBuilder builder = new DefaultModelBuilderFactory().newInstance();
        if (!pom.exists()) {
          publish = false;
          return null;
        }
        DefaultModelBuildingRequest req = new DefaultModelBuildingRequest();
        req.setProcessPlugins(true);
        req.setSystemProperties(System.getProperties());
        req.setModelResolver(new CustomModelResolver(pom.getParentFile()));
        req.setValidationLevel(ModelBuildingRequest.VALIDATION_LEVEL_MINIMAL);
        req.setPomFile(pom);

        result = builder.build(req).getEffectiveModel();
        return result;
      } catch (ModelBuildingException | RuntimeException e) {
        System.out.println(e.getMessage());
        return new Model();
      } finally {
        if (publish) {
          // Serialize the object
          try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(file))) {
            oos.writeObject(new SerializableModel(result));
          } catch (IOException e) {
            System.out.println(e.getMessage());
          }
        }
      }
    }
  }
}
