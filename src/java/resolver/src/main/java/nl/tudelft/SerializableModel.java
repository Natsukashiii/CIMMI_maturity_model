package nl.tudelft;

import java.io.Serializable;
import org.apache.maven.model.Model;

public class SerializableModel extends Model implements Serializable {
  Model model;

  public SerializableModel(Model model) {
    super();
    this.model = model;
  }
}
