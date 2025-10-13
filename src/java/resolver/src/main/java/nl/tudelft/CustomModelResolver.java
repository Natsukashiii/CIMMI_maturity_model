package nl.tudelft;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import org.apache.maven.model.Dependency;
import org.apache.maven.model.Parent;
import org.apache.maven.model.Repository;
import org.apache.maven.model.building.FileModelSource;
import org.apache.maven.model.building.ModelSource2;
import org.apache.maven.model.resolution.InvalidRepositoryException;
import org.apache.maven.model.resolution.ModelResolver;
import org.apache.maven.model.resolution.UnresolvableModelException;

class CustomModelResolver implements ModelResolver {
  private final File baseDir;

  public CustomModelResolver(File baseDir) {
    this.baseDir = baseDir;
  }

  @Override
  public ModelSource2 resolveModel(String groupId, String artifactId, String version)
      throws UnresolvableModelException {
    return resolveModelInternal(groupId, artifactId, version);
  }

  @Override
  public ModelSource2 resolveModel(Parent parent) throws UnresolvableModelException {
    return resolveModelInternal(parent.getGroupId(), parent.getArtifactId(), parent.getVersion());
  }

  public ModelSource2 resolveModelInternal(String groupId, String artifactId, String version)
      throws UnresolvableModelException {
    // 1. First, try resolving the POM locally based on the directory structure
    if (version.equals("${revision}")) {
      version = "LATEST";
    }
    String localPath =
        String.format(
            "%s/%s/%s/%s/pom.xml",
            baseDir.getAbsolutePath(), groupId.replace('.', '/'), artifactId, version);

    File pomFile = new File(localPath);
    if (pomFile.exists()) {
      System.out.println("Found local POM: " + localPath);
      return new FileModelSource(pomFile); // Return the local POM file
    }

    // 2. If local POM doesn't exist, try to check if it is in a parent directory (if applicable)
    // For simplicity, we'll go up one directory and check again. This part can be expanded to
    // handle more complex parent logic
    File parentDir = baseDir.getParentFile();
    if (parentDir != null) {
      String parentPath =
          String.format(
              "%s/%s/%s/%s/pom.xml",
              parentDir.getAbsolutePath(), groupId.replace('.', '/'), artifactId, version);
      pomFile = new File(parentPath);
      if (pomFile.exists()) {
        System.out.println("Found POM in parent directory: " + parentPath);
        return new FileModelSource(pomFile); // Return POM from parent directory
      }
    }

    // 3. If the POM is not found locally, try to resolve it remotely (e.g., from Maven Central)
    return resolveRemotely(groupId, artifactId, version);
  }

  private ModelSource2 resolveRemotely(String groupId, String artifactId, String version)
      throws UnresolvableModelException {
    // Construct the Maven Central URL based on groupId, artifactId, and version
    String baseUrl = "https://repo1.maven.org/maven2";

    // Simulate resolving the model source from Maven Central
    return new ModelSource2() {
      @Override
      public ModelSource2 getRelatedSource(String s) {
        return null;
      }

      public String buildPath(String otherVersion) {
        String path =
            groupId.replace('.', '/')
                + "/"
                + artifactId
                + "/"
                + otherVersion
                + "/"
                + artifactId
                + "-"
                + otherVersion
                + ".pom";
        return baseUrl + "/" + path;
      }

      @Override
      public URI getLocationURI() {
        try {
          return new URI(buildPath(version));
        } catch (URISyntaxException e) {
          throw new RuntimeException(e);
        }
      }

      @Override
      public String getLocation() {
        return buildPath(version);
      }

      @Override
      public InputStream getInputStream() throws IOException {
        URL url = new URL(buildPath(version));
        HttpURLConnection connection;
        try {
          connection = (HttpURLConnection) url.openConnection();
          connection.setRequestMethod("GET");
          if (connection.getResponseCode() == HttpURLConnection.HTTP_OK) {
            return connection.getInputStream();
          } else {
            throw new IOException("Failed to fetch POM file: " + url);
          }
        } catch (IOException e) {
          try {
            String latestVersion = getLatestVersion(baseUrl, groupId, artifactId);
            url = new URL(buildPath(latestVersion));
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            if (connection.getResponseCode() == HttpURLConnection.HTTP_OK) {
              return connection.getInputStream();
            } else {
              throw new IOException();
            }
          } catch (Exception e2) {
            System.err.println("Failed to resolve the latest version: " + e2.getMessage());
            String minimalPom =
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                    + "<project xmlns=\"http://maven.apache.org/POM/4.0.0\"\n"
                    + "         xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n"
                    + "         xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0\n"
                    + "             http://maven.apache.org/xsd/maven-4.0.0.xsd\">\n"
                    + "    <modelVersion>4.0.0</modelVersion>\n"
                    + "    <groupId>"
                    + groupId
                    + "</groupId>\n"
                    + "    <artifactId>"
                    + artifactId
                    + "</artifactId>\n"
                    + "    <version>"
                    + version
                    + "</version>\n"
                    + "    <packaging>pom</packaging>\n"
                    + "</project>";

            // Convert the string into an InputStream
            return new ByteArrayInputStream(minimalPom.getBytes("UTF-8"));
          }
        }
      }
    };
  }

  @Override
  public ModelSource2 resolveModel(Dependency dependency) throws UnresolvableModelException {
    return null;
  }

  @Override
  public void addRepository(Repository repository) throws InvalidRepositoryException {}

  @Override
  public void addRepository(org.apache.maven.model.Repository repository, boolean replace) {
    // No-op
  }

  @Override
  public ModelResolver newCopy() {
    return new CustomModelResolver(baseDir);
  }

  public static String getLatestVersion(String repositoryUrl, String groupId, String artifactId)
      throws Exception {
    // Construct the URL for the metadata.xml
    String metadataUrl =
        repositoryUrl + "/" + groupId.replace('.', '/') + "/" + artifactId + "/maven-metadata.xml";

    // Make an HTTP request to get the metadata XML
    InputStream metadataStream = getInputStream(metadataUrl);

    // Parse the metadata to get the latest version
    BufferedReader reader = new BufferedReader(new InputStreamReader(metadataStream));
    String line;
    String latestVersion = null;
    while ((line = reader.readLine()) != null) {
      if (line.contains("<latest>")) {
        latestVersion = line.replace("<latest>", "").replace("</latest>", "").trim();
        break;
      }
    }
    reader.close();
    return latestVersion;
  }

  private static InputStream getInputStream(String urlString) throws Exception {
    // Open a connection to the URL and get the InputStream
    URL url = new URL(urlString);
    HttpURLConnection connection = (HttpURLConnection) url.openConnection();
    connection.setRequestMethod("GET");
    connection.setConnectTimeout(5000);
    connection.setReadTimeout(5000);
    return connection.getInputStream();
  }
}
